# EUR/USD prediction research and signal software

Everything under `eurusd/` is a self-contained Python project (the rest of the
repository is an unrelated Next.js app).

## Layout

| Path | What |
|------|------|
| `data/raw/` | downloaded archives (HistData zips, CFTC zips). Not committed. |
| `data/processed/` | clean UTC parquet bars: M1, M5, M15, M30, H1, H4, D1 (M1/M5 not committed) |
| `data/macro/` | ECB rates, yields, HICP, CFTC positioning, calendar/event dates, intermarket series |
| `data/DATA_QUALITY.md` | coverage, gaps, outliers, cross-checks against Yahoo and ECB |
| `research/` | strategy catalogue (practitioner) and literature review (academic) with testable hypotheses |
| `src/eurusd/` | library: `data.py`, `features.py`, `backtest.py`, `strategies.py`, `evaluate.py`, signal engine |
| `experiments/` | numbered experiment scripts and their `results/` |
| `reports/` | human-readable findings |

## Data conventions

* HistData 1-minute bars are **bid** prices stamped in New York local time **with** US daylight
  saving (verified against ECB fixings and NFP release spikes; HistData's own "EST" label is wrong).
  `build_data.py` converts with `America/New_York` -> UTC.
* All indexes are tz-aware UTC. The trading day starts at 17:00 New York (22:00 UTC in winter,
  21:00 UTC in summer). Strategies defined in London/New York local time must `tz_convert` first.
* Known data holes: Feb-Jul 2023 is missing 763 hours at the source; 2000-2002 is thin. See `data/DATA_QUALITY.md`.
* 1 pip = 0.0001. Costs: 1.0 pip spread + 0.2 pip slippage per fill unless stated.

## Evaluation protocol (fixed in advance)

* TRAIN 2003-2015: explore, choose parameters.
* VALIDATE 2016-2022: confirm once per strategy family.
* HOLDOUT 2023-today: touched only by the final combined system.
* A strategy survives only if on VALIDATE: avg R > 0, t-stat >= 2, profit factor >= 1.15 after costs,
  >= 60 % of years positive, and the parameter neighbourhood is also positive on TRAIN.
* Intra-bar stop/target ambiguity is resolved pessimistically (stop first) unless M1 data decides.

## Results in one paragraph

See `reports/FINAL_REPORT.md`. Short version: 102 practitioner strategies, 51 academic hypotheses and
19 built-in indicator families were backtested on 26 years of 1-minute data with realistic costs and a
fixed train / validate / holdout protocol. **No single rule survives.** Three weak, mutually uncorrelated
effects (short EUR/USD during London hours, long EUR/USD on FOMC days, follow the CFTC positioning trend)
kept their sign on 2003-2015 and 2016-2022 and are shipped as the live components, but the combination was
flat on the untouched 2023-2026 holdout. Treat the signals as research output, not as a demonstrated edge.

## Running

```bash
cd eurusd
pip install -r requirements.txt
python experiments/test_backtest.py                   # engine sanity tests
PYTHONPATH=src python -m eurusd.cli signals            # live entries with stop-loss / take-profit / size
PYTHONPATH=src python -m eurusd.cli signals --asof 2026-11-05T06:59 --account 10000 --risk 0.005
PYTHONPATH=src python -m eurusd.cli update             # fetch the newest HistData month(s), rebuild bars
PYTHONPATH=src python -m eurusd.cli backtest london_short H1 '{"entry_min":420,"exit_min":780,"stop_adr":1.0}' --period validate
python experiments/01_behaviour_stats.py              # behaviour statistics -> reports/behaviour_stats.md
python experiments/02_grid_builtin.py                 # grid search of the built-in families
```

### Risk engine

Every signal is routed through `src/eurusd/risk.py` before it becomes an order:

* **Sizing**: the smallest of a hard cap (`max_risk_per_trade`), a fractional-Kelly cap from the component's
  validation + holdout trades, a volatility target (HAR one-day forecast) and the remaining open-risk budget;
  halved inside `event_size_cut_hours_before` a high-impact release and blocked inside the release window.
* **Kill switches**: daily loss, monthly loss, drawdown from peak, consecutive losses, stale data, wide spread.
* **Value at risk**: parametric (HAR vol), historical simulation over all NY-close days since 2000 with stops
  honoured, and a Monte Carlo of the strategy mix (1 month / 1 year P&L and drawdown distribution).
* **Stress tests**: the open book replayed through SNB 2015, FOMC/ECB shock days, Brexit, the 2016 election,
  COVID, Ukraine, the 2022 dollar surge and the 2025 tariff gap, plus synthetic 1-3 ADR gaps.
* **Event radar** (next 72 h) and **component health** (live trade R-multiples versus the validation record).

```bash
PYTHONPATH=src python -m eurusd.cli risk --out reports/risk_latest.md     # full report (refreshes recent bars)
PYTHONPATH=src python -m eurusd.cli signals                                # entries with approved size and reasons
PYTHONPATH=src python -m eurusd.cli book add --strategy cot_trend --side short --entry 1.11508 --stop 1.12638 --lots 0.04 --opened 2026-11-08T22:00:00+00:00
PYTHONPATH=src python -m eurusd.cli book close --id 1 --exit-price 1.1180 --closed 2026-11-13T22:00:00+00:00
PYTHONPATH=src python -m eurusd.cli book equity --set 10000
```

Limits live in `config/risk_limits.json`; the position book in `state/book.json` (the user records fills and
closes; the engine never assumes a fill). Recent bars come from Yahoo (`live_data.py`) until HistData publishes
the month; they are flagged in the `source` column. `experiments/test_risk.py` covers sizing caps, event gating,
open-risk budget, stop-aware VaR, stress replay and the kill switches.

Live components are listed in `config/live_strategies.json` (name, timeframe, parameters, validation record).
Macro inputs (`data/macro/`) are refreshed with `PYTHONPATH=src python -m eurusd.macro_fetch`; the CFTC file
and the FOMC calendar must be current for the positioning and FOMC components.
