---
type: dashboard
---

# Dashboard

Requires the free **Dataview** community plugin (Settings → Community
plugins → Browse → "Dataview" → Install → Enable).

## Accounts

```dataview
TABLE phase, status, current_drawdown_used, max_drawdown, days_traded, min_trading_days, last_updated
FROM "Accounts"
WHERE type = "account"
SORT status ASC
```

## Open Risk Flags

Accounts within 20% of their max drawdown or daily loss limit:

```dataview
TABLE current_drawdown_used, max_drawdown, daily_loss_used_today, daily_loss_limit
FROM "Accounts"
WHERE type = "account" AND current_drawdown_used > 0.8 * max_drawdown
```

## This Week's Signals

```dataview
TABLE instrument, direction, entry, outcome, triggered_at
FROM "Signals"
WHERE triggered_at >= date(today) - dur(7 days)
SORT triggered_at DESC
```

## Signal Win Rate (last 30 days, closed only)

```dataview
TABLE length(rows) as count
FROM "Signals"
WHERE outcome != "pending" AND triggered_at >= date(today) - dur(30 days)
GROUP BY outcome
```

## Payout Status

```dataview
TABLE account_id, window_start, window_end, eligible, status
FROM "Payouts"
SORT window_start DESC
```

## Recent Journal Entries

```dataview
LIST
FROM "Journal/Daily"
SORT file.name DESC
LIMIT 7
```
