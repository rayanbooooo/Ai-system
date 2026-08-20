---
type: payout
account_id: APEX-EXAMPLE-01
window_start: 2026-08-15
window_end: 2026-08-29
eligible: false
status: not_requested
amount_requested:
requested_at:
paid_at:
---

# Payout — {{account_id}} — {{window_start}} to {{window_end}}

> `eligible`/window fields are maintained by the payout-eligibility-check
> Routine, computed from `config/rules.yaml#payout_rules` against this
> account's trading history. Verify those rule numbers are current before
> trusting the eligibility flag.

## Checklist

- [ ] Min trading days met
- [ ] Min days since account start / last payout met
- [ ] Consistency rule satisfied (if applicable to this phase)
- [ ] Requested via Apex dashboard
- [ ] Payout received

## Notes
