---
type: daily-journal
date: 2026-08-20
accounts_traded: []
---

# {{date}} — Daily Journal

## Plan

- What am I looking for today? (instruments, sessions, bias)

## Risk Digest

<!-- Auto-appended by the daily-rule-digest Routine. Do not hand-edit this section header. -->

## Setups Alerted Today

```dataview
TABLE instrument, direction, entry, stop_loss, take_profit, outcome
FROM "Signals"
WHERE triggered_at >= date(this.date) AND triggered_at < date(this.date) + dur(1 day)
SORT triggered_at ASC
```

## Trades Taken

| Time | Account | Instrument | Direction | Entry | Exit | Result | Notes |
|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |

## Rule Checks

- [ ] Stayed within daily loss limit on every account
- [ ] No revenge trading / no trades outside the checklist
- [ ] Stopped trading after hitting plan for the day (win or loss)

## Lessons

-
