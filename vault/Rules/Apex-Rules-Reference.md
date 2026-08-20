---
type: rules-reference
last_verified: "UNVERIFIED - fill in the date you checked Apex's official rules"
---

# Apex Trader Funding — Rules Reference

Human-readable mirror of `config/rules.yaml`. **Every number here is a
placeholder** carried over from that file — see its header comment. This
note exists so you have a fast, readable reference while trading; keep it
in sync with `config/rules.yaml` by hand (or regenerate it) whenever you
update the source file.

## How to keep this current

1. Check Apex Trader Funding's current official rules page.
2. Update `config/rules.yaml` first (it's the source of truth used by the
   rule/risk tracker and the daily digest Routine).
3. Update this note to match, and update `last_verified` above.

## Rule Sets

```dataview
TABLE account_size, phase, max_trailing_drawdown, daily_loss_limit, profit_target, min_trading_days, consistency_rule_pct
FROM "Rules"
```

*(This table will populate once rule-set notes are broken out individually;
for now, refer directly to `config/rules.yaml` for the full detail — this
note is the narrative summary, not a second source of truth.)*

## Payout Policy

See `config/rules.yaml#payout_rules` — min days since account start, min
days between payouts, min trading days for first payout, profit split.
