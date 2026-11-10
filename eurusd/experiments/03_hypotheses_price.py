"""Price-only academic hypotheses (research/hypotheses.json) tested on our data.
Each test reports, per period: n, mean return (bp), t-stat, and mean after a
1.2-pip round-trip cost. Output: reports/hypotheses_price.md and
experiments/results/hypotheses_price.csv
"""
import sys
sys.path.insert(0, "/home/user/tapsnap/eurusd/src")
import numpy as np, pandas as pd
from eurusd import features as F
from eurusd.evaluate import SPLITS

D = "/home/user/tapsnap/eurusd/data/processed/"
m5 = pd.read_parquet(D + "EURUSD_M5.parquet")
h1 = pd.read_parquet(D + "EURUSD_H1.parquet")
# clean obvious bad ticks for this analysis (the few 2000-2001 spikes)
for df in (m5, h1):
    bad = (df.close < 0.5) | (df.close > 2.0) | (df.high / df.low > 1.03)
    df.drop(df.index[bad], inplace=True)
COST_PIPS = 1.2
rows = []

def tstat(x):
    x = pd.Series(x).dropna()
    return x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else np.nan

def record(hyp, name, series_bp, price_level=1.15, note=""):
    """series_bp: per-event return in bp of the *traded direction* (positive = profit before cost)."""
    for period, (a, b) in SPLITS.items():
        x = series_bp.loc[a:b].dropna()
        cost_bp = COST_PIPS * 1e-4 / price_level * 1e4
        rows.append(dict(hyp=hyp, test=name, period=period, n=len(x), mean_bp=x.mean(), t=tstat(x),
                         mean_after_cost_bp=x.mean() - cost_bp, t_after_cost=tstat(x - cost_bp),
                         pct_pos=(x > 0).mean(), note=note))

def window_return(df, tz, start, end, side=1):
    """Per-day log return (bp) from the close of the bar ending at local `start` to the close of the
    bar ending at local `end` (HH:MM strings), times in timezone tz. Bars are labelled by start time."""
    loc = df.index.tz_convert(tz)
    step = pd.Timedelta(minutes=5)
    endt = (loc + step)
    key = endt.strftime("%H:%M")
    day = endt.floor("D")
    s = pd.Series(np.log(df.close.values), index=df.index)
    p0 = s[key == start].groupby(day[key == start]).last()
    p1 = s[key == end].groupby(day[key == end]).last()
    r = (p1 - p0).dropna() * 1e4 * side
    r.index = pd.DatetimeIndex(r.index).tz_convert("UTC")
    return r

# ---- H01/H02 local-hours (session) effects on M5 with London/NY local clocks
record("H01", "short EUR/USD 08:00-14:00 London local", window_return(m5, "Europe/London", "08:00", "14:00", -1))
record("H01", "short EUR/USD 07:00-13:00 London local", window_return(m5, "Europe/London", "07:00", "13:00", -1))
record("H02", "long EUR/USD 11:00-16:00 New York local", window_return(m5, "America/New_York", "11:00", "16:00", 1))
record("H02", "long EUR/USD 12:00-17:00 New York local", window_return(m5, "America/New_York", "12:00", "17:00", 1))
# ---- H03/H04/H50 London fix
record("H03", "short 15:00-16:00 London (into WMR fix)", window_return(m5, "Europe/London", "15:00", "16:00", -1))
record("H03", "short 15:30-16:00 London", window_return(m5, "Europe/London", "15:30", "16:00", -1))
record("H04", "long 16:00-16:15 London (post-fix)", window_return(m5, "Europe/London", "16:00", "16:15", 1))
record("H04", "long 16:00-17:00 London", window_return(m5, "Europe/London", "16:00", "17:00", 1))
record("H50", "long 16:05-20:00 London (16:05 approximated by 16:05 bar end)", window_return(m5, "Europe/London", "16:05", "20:00", 1))
# ---- H05 month-end fix reversal
pre = window_return(m5, "Europe/London", "15:45", "16:00", 1)
post = window_return(m5, "Europe/London", "16:00", "16:15", 1)
post30 = window_return(m5, "Europe/London", "16:00", "16:30", 1)
lon_days = pd.Series(pre.index.tz_convert("Europe/London").normalize(), index=pre.index)
ym = lon_days.dt.to_period("M")
is_me = lon_days.groupby(ym).transform("max") == lon_days
fade = (-np.sign(pre) * post).where(is_me)
record("H05", "month-end: fade 15:45-16:00 move over 16:00-16:15", fade.dropna(), note="unit-size fade, sign only")
fade30 = (-np.sign(pre) * post30).where(is_me)
record("H05", "month-end: fade 15:45-16:00 move over 16:00-16:30", fade30.dropna())
pre2 = window_return(m5, "Europe/London", "15:00", "15:45", 1)
cont = (np.sign(pre2) * pre).where(is_me)
record("H05", "month-end: follow 15:00-15:45 move over 15:45-16:00", cont.dropna())
record("H05", "month-end: |15:45-16:00 move| (bp, info only)", pre.abs().where(is_me).dropna(), note="magnitude, not a trade")
record("H51", "all days: fade 15:45-16:00 move over 16:00-16:15", (-np.sign(pre) * post).dropna())
# ---- H06 ECB fix 14:15 CET
record("H06", "short 13:45-14:15 CET (into ECB fix)", window_return(m5, "Europe/Berlin", "13:45", "14:15", -1))
record("H06", "long 14:15-14:45 CET (after ECB fix)", window_return(m5, "Europe/Berlin", "14:15", "14:45", 1))
# ---- H07 Tokyo fix 09:55 JST
record("H07", "short 09:25-09:55 JST (into Tokyo fix)", window_return(m5, "Asia/Tokyo", "09:25", "09:55", -1))
record("H07", "long 09:55-10:25 JST (after Tokyo fix)", window_return(m5, "Asia/Tokyo", "09:55", "10:25", 1))
tk = window_return(m5, "Asia/Tokyo", "09:25", "09:55", -1)
jd = pd.Series(tk.index.tz_convert("Asia/Tokyo").day, index=tk.index)
gotobi = jd.isin([5, 10, 15, 20, 25]) | (pd.Series(tk.index.tz_convert("Asia/Tokyo").normalize(), index=tk.index).groupby(pd.Series(tk.index.tz_convert("Asia/Tokyo").to_period("M"), index=tk.index)).transform("max") == pd.Series(tk.index.tz_convert("Asia/Tokyo").normalize(), index=tk.index))
record("H07", "short 09:25-09:55 JST on gotobi days", tk.where(gotobi).dropna())

# ---- H15/H16 weekend gaps (NY-close days, 22:00 UTC boundary)
d = F.daily_ohlc(h1, 22)
d = d[d["n"] >= 10]
d["dow"] = d.index.dayofweek  # label 6 = Sunday 22:00 start = Monday session
d["atr20"] = F.atr(d, 20).shift(1)
d["ret"] = np.log(d.close / d.open) * 1e4
mon = d[d.dow == 6].copy()
prev_close = d.close.shift(1).reindex(mon.index)
mon["gap"] = np.log(mon.open / prev_close) * 1e4
mon["gap_atr"] = (mon.open - prev_close).abs() / mon["atr20"]
# forward returns from Monday open: 1 day (to Monday close), 2 days, 5 days (to Friday close)
pos = d.index.get_indexer(mon.index)
for k in (1, 2, 5):
    fwd = np.log(d.close.values[np.minimum(pos + k - 1, len(d) - 1)] / mon.open.values) * 1e4
    mon[f"fwd{k}"] = fwd
large = mon["gap_atr"] > 0.2  # |gap| > 1.0 x ATR/5
for k in (1, 2, 5):
    x = (-np.sign(mon.gap) * mon[f"fwd{k}"]).where(large)
    record("H15", f"large weekend gap (>ATR20/5): fade, hold {k} day(s)", x.dropna(), note="unit size, fade direction")
small = (mon.gap.abs() > 0) & (mon["gap_atr"] < 0.5)
x = (-np.sign(mon.gap) * mon["fwd1"]).where(small)
record("H16", "small weekend gap (<0.5 ATR20): fade, hold Monday", x.dropna())
record("H16", "info: mean |gap| bp", mon.gap.abs(), note="magnitude")
# ---- H17/H19/H18 time-series momentum, monthly rebalance (spot only, carry omitted until rates data)
dm = d.close.resample("ME").last()
lr = np.log(dm).diff() * 1e4
for lb, hyp in ((12, "H17"), (1, "H19"), (3, "H18"), (6, "H18")):
    sig = np.sign(np.log(dm / dm.shift(lb))).shift(1)
    record(hyp, f"TSMOM lookback {lb}m, hold 1m (spot only)", (sig * lr).dropna(), note="monthly return of signed position")
# daily-frequency TSMOM: sign of past 252/63/21-day return, hold 1 day
for lb in (21, 63, 252):
    sig = np.sign(np.log(d.close / d.close.shift(lb))).shift(1)
    record("H18", f"daily TSMOM lookback {lb}d, hold 1 day", (sig * np.log(d.close / d.close.shift(1)) * 1e4).dropna())
# ---- H41 turn of month day slots (NY-close days, calendar month)
dd = d[d.dow != 5].copy()
dd["r"] = np.log(dd.close / dd.close.shift(1)) * 1e4
dd["ym"] = dd.index.to_period("M")
dd["from_start"] = dd.groupby("ym").cumcount() + 1
dd["from_end"] = dd.groupby("ym")["r"].transform("size") - dd["from_start"] + 1  # 1 = last day (T)
for slot in range(-5, 6):
    if slot <= 0:
        mask = dd["from_end"] == (1 - slot)
        lab = f"T{slot}" if slot < 0 else "T (last day)"
    else:
        mask = dd["from_start"] == slot
        lab = f"T+{slot}"
    record("H41", f"long EUR/USD on day {lab}", dd["r"].where(mask).dropna())
tom = dd[(dd.from_end <= 2) | (dd.from_start <= 3)]
record("H41", "long T-1..T+3 (sum of 5 days)", tom.groupby("ym")["r"].sum().pipe(lambda s: s.set_axis(s.index.to_timestamp(how="end").tz_localize("UTC"))))
# ---- H36 GK vol regime split of the H01 effect
gk = 0.5 * np.log(d.high / d.low) ** 2 - (2 * np.log(2) - 1) * np.log(d.close / d.open) ** 2
gk10 = gk.rolling(10).mean()
thr = gk10.rolling(252).quantile(0.6)
regime = (gk10 > thr).shift(1)
lon = window_return(m5, "Europe/London", "08:00", "14:00", -1)
reg_at = regime.reindex(lon.index.floor("D") + pd.Timedelta(hours=22) - pd.Timedelta(days=1))
reg_at.index = lon.index
record("H36", "H01 short 08-14 London in HIGH GK vol regime", lon.where(reg_at == True).dropna())
record("H36", "H01 short 08-14 London in LOW GK vol regime", lon.where(reg_at == False).dropna())

out = pd.DataFrame(rows)
out.to_csv("/home/user/tapsnap/eurusd/experiments/results/hypotheses_price.csv", index=False)
piv = out.pivot_table(index=["hyp", "test"], columns="period", values=["n", "mean_bp", "t", "t_after_cost"], sort=False)
piv = piv.reindex(columns=["train", "validate", "holdout"], level=1)
md = "# Price-only hypothesis tests (bp per event; cost = 1.2 pips round trip)\n\n" + piv.round(2).to_markdown()
open("/home/user/tapsnap/eurusd/reports/hypotheses_price.md", "w").write(md)
pd.set_option("display.width", 250)
print(piv.round(2).to_string())
