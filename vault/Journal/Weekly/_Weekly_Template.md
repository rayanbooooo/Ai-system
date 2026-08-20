---
type: weekly-journal
week: 2026-W34
---

# Week {{week}} — Rollup

<!-- Auto-authored by the weekly-journal-rollup Routine from the week's
     daily notes and signals. Safe to hand-edit after it runs. -->

## Summary

## Setups This Week

```dataview
TABLE instrument, direction, outcome
FROM "Signals"
WHERE triggered_at >= date(this.file.name, "YYYY-[W]WW") AND triggered_at < date(this.file.name, "YYYY-[W]WW") + dur(7 days)
SORT triggered_at ASC
```

## Account Progress

```dataview
TABLE phase, current_drawdown_used, max_drawdown, days_traded, min_trading_days
FROM "Accounts"
```

## What Worked / What Didn't

## Focus For Next Week

-
