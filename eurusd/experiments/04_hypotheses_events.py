"""Event hypotheses: FOMC (H08-H10, C07, C08), ECB (H14, C09, H48), NFP/CPI (H11-H13, V05, V06).
Windows are measured on M5 bid closes (true UTC). Output: reports/hypotheses_events.md
"""
import sys
sys.path.insert(0, "/home/user/tapsnap/eurusd/src")
import numpy as np, pandas as pd
from eurusd.evaluate import SPLITS
from eurusd.backtest import Order, CostModel, run_backtest

D = "/home/user/tapsnap/eurusd/data/"
m5 = pd.read_parquet(D + "processed/EURUSD_M5.parquet").loc["2003":]
close = m5["close"]
COST_BP = 1.2 * 1e-4 / 1.15 * 1e4
rows = []

def tstat(x):
    x = pd.Series(x).dropna()
    return x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else np.nan

def px_at(t):
    """last M5 close at or before t (bar labelled by start => use bar whose END <= t: label <= t-5min)."""
    i = close.index.searchsorted(t - pd.Timedelta(minutes=5), side="right") - 1
    return close.iat[i] if i >= 0 else np.nan

def ret(t0, t1):
    return (np.log(px_at(t1)) - np.log(px_at(t0))) * 1e4

def record(hyp, name, s, note=""):
    s = pd.Series(s).dropna()
    for period, (a, b) in SPLITS.items():
        x = s.loc[a:b]
        rows.append(dict(hyp=hyp, test=name, period=period, n=len(x), mean_bp=x.mean(), t=tstat(x),
                         t_after_cost=tstat(x - COST_BP), pct_pos=(x > 0).mean(), note=note))

def series(times, f):
    out = {}
    for t in times:
        try:
            v = f(t)
        except Exception:
            v = np.nan
        out[t] = v
    return pd.Series(out)

H = pd.Timedelta(hours=1); M = pd.Timedelta(minutes=1); DAY = pd.Timedelta(days=1)

# ---------------- FOMC
fomc = pd.read_csv(D + "macro/fomc_decisions.csv", parse_dates=["statement_utc"])
fomc = fomc[(fomc.scheduled == True) & (fomc.status == "held")]
ft = [t for t in pd.to_datetime(fomc.statement_utc, utc=True) if pd.Timestamp("2003-01-01", tz="UTC") <= t <= close.index[-1] - DAY]
# NY-close reference: 21:00/22:00 UTC previous day ~ use statement - 20h as 'T-1 close' approximation -> use exact 17:00 NY
def ny_close(t, days_back=0):
    loc = t.tz_convert("America/New_York").normalize() + pd.Timedelta(hours=17) - pd.Timedelta(days=days_back)
    return loc.tz_convert("UTC")
record("H08", "FOMC day: long EUR/USD T-1 NY close -> T NY close", series(ft, lambda t: ret(ny_close(t, 1), ny_close(t, 0))))
record("H08", "FOMC: long statement-1h -> statement+3h", series(ft, lambda t: ret(t - H, t + 3 * H)))
record("H09", "pre-FOMC: long T-3 NY close -> statement-1h (unconditional)", series(ft, lambda t: ret(ny_close(t, 3), t - H)))
dgs2 = pd.read_csv(D + "macro/fred_DGS2.csv", parse_dates=["date"]).set_index("date")["value"].dropna()
def exp_sign(t):  # proxy for policy expectation: 2y yield change over 20 trading days ending T-3
    d = t.tz_convert("America/New_York").normalize().tz_localize(None) - pd.Timedelta(days=3)
    s = dgs2.loc[:d]
    return np.sign(s.iloc[-1] - s.iloc[-21]) if len(s) > 21 else np.nan
record("H09", "pre-FOMC conditional: short EUR/USD T-3 -> stmt-1h if US 2y rose over prior 20d, else long", series(ft, lambda t: -exp_sign(t) * ret(ny_close(t, 3), t - H)), note="2y-yield change as proxy for hike/cut signal")
record("H10", "post-FOMC: fade stmt->stmt+1h move over stmt+1h -> stmt+24h", series(ft, lambda t: -np.sign(ret(t, t + H)) * ret(t + H, t + 24 * H)))
record("H10", "post-FOMC: fade stmt->stmt+1h move over stmt+12h -> stmt+24h", series(ft, lambda t: -np.sign(ret(t, t + H)) * ret(t + 12 * H, t + 24 * H)))
record("C08", "FOMC: continue stmt->stmt+30m move over stmt+30m -> stmt+2h (press-conf)", series(ft, lambda t: np.sign(ret(t, t + 30 * M)) * ret(t + 30 * M, t + 2 * H)))
record("C08", "info: |stmt -> stmt+1h| move bp", series(ft, lambda t: abs(ret(t, t + H))), note="magnitude")

# ---------------- ECB
ecb = pd.read_csv(D + "macro/ecb_decisions.csv", parse_dates=["decision_utc", "press_conference_utc"])
_lo, _hi = pd.Timestamp("2003-01-01", tz="UTC"), close.index[-1] - DAY
et = [(pd.Timestamp(a).tz_convert("UTC"), pd.Timestamp(b).tz_convert("UTC")) for a, b in zip(ecb.decision_utc, ecb.press_conference_utc) if _lo <= pd.Timestamp(a).tz_convert("UTC") <= _hi]
dec = [a for a, b in et]
pc = {a: b for a, b in et}
record("H14", "ECB: continue decision->press+15m move over press+15m -> press+1h", series(dec, lambda t: np.sign(ret(t, pc[t] + 15 * M)) * ret(pc[t] + 15 * M, pc[t] + H)))
record("H14", "ECB: continue decision->press+1h move over press+1h -> press+4h", series(dec, lambda t: np.sign(ret(t, pc[t] + H)) * ret(pc[t] + H, pc[t] + 4 * H)))
record("C09", "ECB: fade decision->decision+15m move over decision+15m -> press conf start", series(dec, lambda t: -np.sign(ret(t, t + 15 * M)) * ret(t + 15 * M, pc[t])))
record("C09", "ECB day: long EUR/USD T-1 NY close -> T NY close", series(dec, lambda t: ret(ny_close(t, 1), ny_close(t, 0))))
record("H48", "info: |decision -> press+1h| move bp", series(dec, lambda t: abs(ret(t, pc[t] + H))), note="magnitude")

# ---------------- NFP / CPI
ev = pd.read_csv(D + "macro/events.csv")
ev = ev[ev.has_time == True].copy()
ev["t"] = pd.to_datetime(ev.datetime_utc, utc=True)
def parse_num(x):
    if pd.isna(x): return np.nan
    s = str(x).replace("%", "").replace(",", "")
    mult = 1000 if s.endswith("K") else (1e6 if s.endswith("M") else 1)
    try: return float(s.rstrip("KMB")) * mult
    except ValueError: return np.nan
ff = ev[ev.source.str.startswith("ff_")].copy()
ff["a"] = ff.actual.map(parse_num); ff["f"] = ff.forecast.map(parse_num)
def releases(name, currency="USD"):
    s = ff[(ff.currency == currency) & (ff.event.str.contains(name, na=False, regex=False)) & ff.a.notna() & ff.f.notna()]
    s = s[~s.source.eq("ff_2026_fxdesk_lowq")]  # unreliable times
    s = s.drop_duplicates("t")
    s = s[s.t.dt.hour.isin([12, 13])]  # 08:30 ET releases only
    return s.sort_values("t")
for name, label in (("Non-Farm Employment Change", "NFP"), ("CPI m/m", "CPI m/m"), ("Core CPI m/m", "Core CPI")):
    r = releases(name)
    times = list(r.t)
    surprise = pd.Series(np.sign(r.a.values - r.f.values), index=r.t)
    record("H11/H12", f"{label}: info |release -> +5m| bp", series(times, lambda t: abs(ret(t, t + 5 * M))), note=f"n releases with actual+forecast={len(r)}")
    record("H11/H12", f"{label}: trade surprise sign at +5m, hold to +1h (USD up on positive surprise => short EUR/USD)", series(times, lambda t: -surprise[t] * ret(t + 5 * M, t + H)))
    record("H11/H12", f"{label}: trade surprise sign at +5m, hold to +4h", series(times, lambda t: -surprise[t] * ret(t + 5 * M, t + 4 * H)))
    record("H13", f"{label}: continue +5m jump over +5m -> +1h", series(times, lambda t: np.sign(ret(t, t + 5 * M)) * ret(t + 5 * M, t + H)))
    record("H13", f"{label}: continue +5m jump over +5m -> NY close", series(times, lambda t: np.sign(ret(t, t + 5 * M)) * ret(t + 5 * M, ny_close(t, 0))))
    record("H13", f"{label}: continue first 30m move over +30m -> NY close", series(times, lambda t: np.sign(ret(t, t + 30 * M)) * ret(t + 30 * M, ny_close(t, 0))))
    # V06: price back to pre-release level within 1h
    def back_within(t, mins=60):
        p0 = px_at(t)
        seg = m5.loc[t + 5 * M: t + pd.Timedelta(minutes=mins)]
        jump = px_at(t + 5 * M) - p0
        if jump > 0: return float((seg.low <= p0).any())
        if jump < 0: return float((seg.high >= p0).any())
        return np.nan
    record("V06", f"{label}: P(price returns to pre-release level within 1h)", series(times, back_within), note="base rate, not a return")
    record("V06", f"{label}: fade +5m jump over +5m -> +1h", series(times, lambda t: -np.sign(ret(t, t + 5 * M)) * ret(t + 5 * M, t + H)))
    # V05 straddle via the engine
    for dist, sl, tp in ((10, 20, 40), (15, 25, 50), (8, 15, 30)):
        orders = []
        for t in times:
            i = m5.index.searchsorted(t) - 1  # bar whose close is just before release
            if i < 0 or m5.index[i] + 5 * M != t: continue
            p = close.iat[i]
            exit_i = i + 24  # 2 hours
            orders.append(Order(i=i, side=1, entry_type="stop", entry_price=p + dist * 1e-4, sl=p + (dist - sl) * 1e-4, tp=p + (dist + tp) * 1e-4, expiry_bars=3, exit_i=exit_i, tag="straddle"))
            orders.append(Order(i=i, side=-1, entry_type="stop", entry_price=p - dist * 1e-4, sl=p - (dist - sl) * 1e-4, tp=p - (dist + tp) * 1e-4, expiry_bars=3, exit_i=exit_i, tag="straddle"))
        res = run_backtest(m5, orders, CostModel(spread_pips=3.0, slippage_pips=3.0))  # wide spread/slippage at release
        if not res.tdf.empty:
            s = pd.Series(res.tdf.pips.values, index=res.tdf.entry_time.values)
            for period, (a, b) in SPLITS.items():
                x = s.loc[a:b]
                rows.append(dict(hyp="V05", test=f"{label}: straddle +/-{dist} pips, SL {sl}, TP {tp}, 2h max (pips, 3+3 pip cost)", period=period, n=len(x), mean_bp=x.mean(), t=tstat(x), t_after_cost=tstat(x), pct_pos=(x > 0).mean(), note="pips not bp; costs included"))

out = pd.DataFrame(rows)
out.to_csv("/home/user/tapsnap/eurusd/experiments/results/hypotheses_events.csv", index=False)
piv = out.pivot_table(index=["hyp", "test"], columns="period", values=["n", "mean_bp", "t", "t_after_cost"], sort=False).reindex(columns=["train", "validate", "holdout"], level=1)
open("/home/user/tapsnap/eurusd/reports/hypotheses_events.md", "w").write("# Event hypothesis tests (bp per event unless noted; cost = 1.2 pips)\n\n" + piv.round(2).to_markdown())
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
print(piv.round(2).to_string())
