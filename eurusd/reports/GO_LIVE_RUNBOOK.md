# Getting the EUR/USD system properly underway

What exists: a clean 26-year dataset, a correct engine, one walk-forward-validated daily exposure (Sharpe
~0.6 since 2016, ~0.35 since 2023, not significant after multiple-testing correction), a risk engine with
sizing, VaR, stress, event gating and kill switches, a daily brief and a weekly outlook, and a forward-test log.
What does not exist: a proven edge. The plan below treats the next months as the test that decides that.

## Phase 1 - forward test on paper (now, 3 to 6 months)
1. Let the daily brief run every weekday (22:41 UTC). Each run refreshes positioning (CFTC), ECB yields and
   FRED mirrors, recomputes the target, and appends a row to `state/signal_log.csv`.
2. Record the signal log somewhere persistent (see "Where it runs" below): the forward record is the product
   of this phase. 60+ sessions give a first read; 120+ give a usable one.
3. Watch three numbers in the brief: `action` (HOLD/REBALANCE), `Limits`, and the data age. Nothing else.
4. Monthly: compare the realised P&L per unit of the logged targets with the out-of-sample record
   (0.58 bp per session per unit, sd 16 bp). The risk report's component-health block does this once there are
   live rows in the book.

## Phase 2 - small real money (only if phase 1 is not negative)
1. Broker with a REST API and sub-1-pip EUR/USD spreads (OANDA v20, IG, Interactive Brokers; the research cost
   assumption is 1.2 pips per round trip; at 2+ pips the edge is gone).
2. Fund an account and set `book equity`. Start at the configured 8 % vol target or lower; one unit is then
   about 1.4 x equity in notional, i.e. ~0.14 lots per 10,000.
3. Trade exactly what the brief says: rebalance only on REBALANCE, place the disaster stop it prints, record
   every fill with `book add` / `book close` so the kill switches and health check see real numbers.
4. Scale only on evidence: double size after 6 months of live Sharpe >= 0.4 and no kill-switch breach; halve
   it after any 10 % drawdown; stop after a health alert (live mean two standard errors below the record).

## Phase 3 - automation (after phase 2 is stable)
1. Add a broker adapter (`src/eurusd/broker_<name>.py`): read positions, place market orders with a stop,
   write fills to the book. The brief already computes the exact order; the adapter only executes it.
2. Move the daily run to wherever the adapter's credentials live (the desktop app with a local folder, or a
   small VPS). The cloud scheduled session cannot hold secrets or persist the book.

## Where it runs (decide this first)
* Cloud scheduled task (current): works for the brief and outlook, but the session is thrown away after each
  run and cannot push, so `state/book.json` and `state/signal_log.csv` do not persist. Fine for reading, not for
  a forward record.
* Your own computer via the desktop app with this folder (the same model as your BTC/USDT brief): code, bars,
  book and log persist; a broker API key can live there; the same two commands run on a local schedule.
  Recommended.

## Research, on a leash
The next real gains need new information, not more modelling: order flow (CME 6E depth or a broker's own flow),
options positioning (risk reversals), and real-time rate expectations (OIS). Each is a new "arm" under the same
walk-forward protocol (`experiments/HOWTO_ARMS.md`); nothing goes live without clearing it. Budget one arm per
quarter and resist re-tuning the live exposure on short-term results.

## Daily checklist (two minutes)
- Read the brief. If HOLD and ALL CLEAR: done.
- If REBALANCE: adjust to the printed lots and stop, then `book add`/`book close` with the fill.
- If BREACHED or HALTED: flatten per the kill-switch rules, then review before re-enabling.
- Friday: the positioning data updates at 20:30 UTC; Monday's brief is the first to reflect it.
