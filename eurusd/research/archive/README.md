# Archive: research code that did NOT survive

Kept for reproducibility only; nothing here is imported by the runtime.

* `strategies/` round-1 catalogue strategies (session/calendar, trend/volatility/price-action, mean-reversion):
  152 families, none survived validation. Their reports: `reports/catalogue_*.md`, results: `experiments/results/`.
  To re-run: copy a module back into `src/eurusd/` (they register into `eurusd.strategies.REGISTRY` on import)
  and run the matching driver from `experiments/`.
* `arms/` round-2 arms that failed: daily machine learning (clean negative, technicals negative after cost),
  intraday machine learning (no tradable context effect; its one positive is a rollover-hour artefact),
  event-driven (surprises are absorbed in the release bar). Reports: `reports/arm_*.md`; OOS streams:
  `experiments/results/arms/`.
