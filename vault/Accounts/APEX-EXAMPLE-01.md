---
type: account
account_id: APEX-EXAMPLE-01
size: 50000
phase: evaluation
status: active
rules_ref: eval_50k
tradovate_account_id: ""
tradovate_env: demo
max_drawdown: 2500
drawdown_mode: trailing_to_threshold
daily_loss_limit:
profit_target: 3000
min_trading_days: 7
consistency_rule_pct: 30
current_drawdown_used: 340
daily_loss_used_today: 0
days_traded: 3
start_date: 2026-08-20
last_updated: 2026-01-01T09:49:00-05:00
---

# APEX-EXAMPLE-01

> **This is DEMO data** — seeded so the vault isn't empty on first open, not
> a real account. Delete or overwrite this note once you fill in your real
> account(s) in `config/accounts.yaml`. All numeric rule values above are
> still placeholders copied from `config/rules.yaml` — verify against
> Apex's current official terms before relying on this for pass/fail
> decisions.

## Status

- Phase: `= this.phase`
- Drawdown used: `= this.current_drawdown_used` / `= this.max_drawdown`
- Days traded: `= this.days_traded` / `= this.min_trading_days`

## Notes

Demo account showing what a tracked Apex evaluation looks like once the
scanner and Routines are writing real data.

## Recent Signals

```dataview
TABLE instrument, direction, entry, stop_loss, take_profit, outcome
FROM "Signals"
WHERE contains(accounts_notified, this.account_id)
SORT triggered_at DESC
LIMIT 10
```

## Payout History

```dataview
TABLE window_start, window_end, status, amount_requested
FROM "Payouts"
WHERE account_id = this.account_id
SORT window_start DESC
```
