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

* HistData 1-minute bars are **bid** prices in EST (UTC-5, no DST). We shift to UTC.
* All indexes are tz-aware UTC. "NY-close days" start at 22:00 UTC.
* 1 pip = 0.0001. Costs: 1.0 pip spread + 0.2 pip slippage per fill unless stated.

## Evaluation protocol (fixed in advance)

* TRAIN 2003-2015: explore, choose parameters.
* VALIDATE 2016-2022: confirm once per strategy family.
* HOLDOUT 2023-today: touched only by the final combined system.
* A strategy survives only if on VALIDATE: avg R > 0, t-stat >= 2, profit factor >= 1.15 after costs,
  >= 60 % of years positive, and the parameter neighbourhood is also positive on TRAIN.
* Intra-bar stop/target ambiguity is resolved pessimistically (stop first) unless M1 data decides.

## Running

```bash
cd eurusd
pip install -r requirements.txt
python experiments/test_backtest.py          # engine sanity tests
python experiments/01_behaviour_stats.py     # behaviour statistics -> reports/behaviour_stats.md
python experiments/02_grid_builtin.py        # grid search of built-in families
```
